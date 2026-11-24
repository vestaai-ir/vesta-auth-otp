// Copyright 2026 Vesta AI (https://vestaai.ir)
// License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

/** Persian (۰-۹) and Arabic (٠-٩) digits as ASCII digits. */
export function asciiDigits(text) {
    return (text || "")
        .replace(/[۰-۹]/g, (d) => String(d.charCodeAt(0) - 0x06f0))
        .replace(/[٠-٩]/g, (d) => String(d.charCodeAt(0) - 0x0660));
}

function isPersian() {
    return (document.documentElement.lang || "").toLowerCase().startsWith("fa");
}

function localDigits(text) {
    return isPersian() ? String(text).replace(/[0-9]/g, (d) => "۰۱۲۳۴۵۶۷۸۹"[d]) : String(text);
}

/**
 * The card of «Login with mobile» (login page, sign-up page, /my/account): the mobile number, then the code sent
 * by SMS and Bale, then a name when the number has no account. A right code gives a one-time token that the hidden
 * form posts to /web/login, so the session is opened by Odoo itself (two-factor authentication included).
 */
export class VestaOtpLogin extends Interaction {
    static selector = ".o_vesta_otp";
    dynamicContent = {
        ".o_vo_phone_form": { "t-on-submit.prevent.noUpdate": this.locked(this.onPhoneSubmit, true) },
        ".o_vo_code_form": { "t-on-submit.prevent.noUpdate": this.locked(this.onCodeSubmit, true) },
        ".o_vo_name_form": { "t-on-submit.prevent.noUpdate": this.locked(this.onNameSubmit, true) },
        ".o_vo_code": { "t-on-input.noUpdate": this.onCodeInput },
        ".o_vo_input": { "t-on-input.noUpdate": this.clearMessages },
        ".o_vo_edit": { "t-on-click.noUpdate": this.onEdit },
        ".o_vo_resend": { "t-on-click.noUpdate": this.locked(this.onResend, true) },
        _document: { "t-on-click.noUpdate": this.onDocumentClick },
    };

    setup() {
        this.mode = this.el.dataset.mode || "login";
        this.codeLength = parseInt(this.el.dataset.codeLength, 10) || 6;
        this.challenge = null;
        this.token = null;
        this.phone = "";
        this.timer = null;
        this.webOtp = null;
        this.codeInput = this.el.querySelector(".o_vo_code");
    }

    start() {
        if (this.el.classList.contains("o_vo_active")) {
            this.el.querySelector(".o_vo_step[data-step=phone] input")?.focus();
        }
    }

    destroy() {
        this.stopTimer();
        this.webOtp?.abort();
    }

    // ------------------------------------------------------------------
    // Steps and messages
    // ------------------------------------------------------------------

    showStep(step) {
        for (const el of this.el.querySelectorAll(".o_vo_step")) {
            el.classList.toggle("d-none", el.dataset.step !== step);
        }
        const input = this.el.querySelector(`.o_vo_step[data-step=${step}] input`);
        input?.focus();
        if (step !== "code") {
            this.stopTimer();
            this.webOtp?.abort();
        }
    }

    showError(text) {
        const el = this.el.querySelector(".o_vo_error");
        el.textContent = text || "";
        el.classList.toggle("d-none", !text);
    }

    showSuccess(text) {
        const el = this.el.querySelector(".o_vo_success");
        el.textContent = text || "";
        el.classList.toggle("d-none", !text);
    }

    clearMessages() {
        this.showError("");
        this.showSuccess("");
    }

    // ------------------------------------------------------------------
    // Mode: mobile or password
    // ------------------------------------------------------------------

    onDocumentClick(ev) {
        const button = ev.target.closest(".o_vo_switch");
        if (!button || this.mode === "change") {
            return;
        }
        // the buttons of the card say where they go; the mobile login among Odoo's ways to log in is a link
        ev.preventDefault();
        const otp = button.dataset.voSwitch === "otp" || button.classList.contains("o_vo_to_otp");
        this.el.classList.toggle("o_vo_active", otp);
        if (otp) {
            this.el.querySelector(".o_vo_step:not(.d-none) input")?.focus();
        } else {
            document.querySelector(".oe_login_form input:not([type=hidden]), .oe_signup_form input:not([type=hidden])")?.focus();
        }
    }

    // ------------------------------------------------------------------
    // Step 1: the mobile number
    // ------------------------------------------------------------------

    async onPhoneSubmit() {
        const input = this.el.querySelector("input[name=vo_phone]");
        const phone = asciiDigits(input.value).replace(/[^\d+]/g, "");
        if (!phone) {
            input.focus();
            return;
        }
        this.phone = phone;
        await this.requestCode();
    }

    async requestCode() {
        this.clearMessages();
        const result = await this.waitFor(
            rpc("/vesta_otp/send", { phone: this.phone, purpose: this.mode === "change" ? "change" : "login" })
        );
        if (!result.ok) {
            this.showError(result.error);
            if (result.resend_in && this.challenge) {
                this.startTimer(result.resend_in);
            }
            return false;
        }
        this.challenge = result.challenge;
        this.codeLength = result.code_length || this.codeLength;
        this.el.querySelector(".o_vo_phone_display").textContent = result.phone_display;
        this.el.querySelector(".o_vo_sent").textContent = result.message || "";
        const hint = this.el.querySelector(".o_vo_hint");
        hint.textContent = result.hint || "";
        hint.classList.toggle("d-none", !result.hint);
        this.codeInput.value = "";
        this.codeInput.maxLength = this.codeLength;
        this.showStep("code");
        this.startTimer(result.resend_in || 0);
        this.listenWebOtp();
        return true;
    }

    // ------------------------------------------------------------------
    // Step 2: the code
    // ------------------------------------------------------------------

    onCodeInput() {
        this.showError("");
        const digits = asciiDigits(this.codeInput.value).replace(/\D/g, "").slice(0, this.codeLength);
        if (digits !== this.codeInput.value) {
            this.codeInput.value = digits;
        }
        if (digits.length === this.codeLength) {
            this.el.querySelector(".o_vo_code_form button[type=submit]").click();
        }
    }

    async onCodeSubmit() {
        const code = asciiDigits(this.codeInput.value).replace(/\D/g, "");
        if (code.length !== this.codeLength) {
            this.codeInput.focus();
            return;
        }
        const result = await this.waitFor(rpc("/vesta_otp/verify", { challenge: this.challenge, code }));
        this.handleVerified(result);
    }

    handleVerified(result) {
        if (!result.ok) {
            this.showError(result.error);
            this.codeInput.value = "";
            if (result.dead) {
                this.challenge = null;
                this.stopTimer();
                this.showResend(true);
            }
            this.codeInput.focus();
            return;
        }
        this.token = result.token;
        if (result.action === "signup") {
            this.showStep("name");
        } else if (result.action === "changed") {
            this.showStep("phone");
            this.el.querySelector("input[name=vo_phone]").value = "";
            this.showSuccess(result.message);
            const value = document.querySelector(".o_vo_account_value");
            if (value) {
                value.textContent = result.phone_display;
            }
            window.setTimeout(() => window.location.reload(), 1500);
        } else {
            this.login();
        }
    }

    login() {
        const form = this.el.querySelector(".o_vo_login_form");
        form.querySelector("input[name=otp_token]").value = this.token;
        this.el.classList.add("o_vo_busy");
        form.submit();
    }

    async onResend() {
        this.codeInput.value = "";
        await this.requestCode();
    }

    onEdit() {
        this.challenge = null;
        this.clearMessages();
        this.showStep("phone");
    }

    // ------------------------------------------------------------------
    // Step 3: the name of a new account
    // ------------------------------------------------------------------

    async onNameSubmit() {
        const input = this.el.querySelector("input[name=vo_name]");
        const name = input.value.trim();
        if (name.length < 2) {
            input.focus();
            return;
        }
        const result = await this.waitFor(
            rpc("/vesta_otp/signup", { challenge: this.challenge, token: this.token, name })
        );
        if (!result.ok) {
            this.showError(result.error);
            if (result.dead) {
                this.showStep("phone");
            }
            return;
        }
        this.token = result.token;
        this.login();
    }

    // ------------------------------------------------------------------
    // Resend countdown, WebOTP
    // ------------------------------------------------------------------

    showResend(ready) {
        this.el.querySelector(".o_vo_wait").classList.toggle("d-none", ready);
        this.el.querySelector(".o_vo_resend").classList.toggle("d-none", !ready);
    }

    startTimer(seconds) {
        this.stopTimer();
        let left = Math.max(0, Math.round(seconds));
        const timerEl = this.el.querySelector(".o_vo_timer");
        const render = () => {
            const minutes = Math.floor(left / 60);
            const rest = String(left % 60).padStart(2, "0");
            timerEl.textContent = localDigits(`${minutes}:${rest}`);
        };
        if (!left) {
            this.showResend(true);
            return;
        }
        render();
        this.showResend(false);
        this.timer = setInterval(() => {
            left -= 1;
            if (left <= 0) {
                this.stopTimer();
                this.showResend(true);
            } else {
                render();
            }
        }, 1000);
    }

    stopTimer() {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
    }

    listenWebOtp() {
        if (!("OTPCredential" in window) || !navigator.credentials) {
            return;
        }
        this.webOtp?.abort();
        this.webOtp = new AbortController();
        navigator.credentials
            .get({ otp: { transport: ["sms"] }, signal: this.webOtp.signal })
            .then((otp) => {
                if (otp?.code && !this.isDestroyed) {
                    this.codeInput.value = otp.code;
                    this.onCodeInput();
                }
            })
            .catch(() => {
                // no SMS read (aborted, refused or not supported): the code is typed
            });
    }
}

registry.category("public.interactions").add("vesta_auth_otp.otp_login", VestaOtpLogin);
