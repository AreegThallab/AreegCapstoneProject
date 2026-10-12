
document.addEventListener("DOMContentLoaded", () => {
    // =========================================
    // 01. COPY PRIVATE INVITATION LINK
    // =========================================
    const copyButton = document.getElementById("copy-private-invite");
    const inviteInput = document.getElementById("private-invite-url");
    const feedback = document.getElementById("private-invite-feedback");
    if (copyButton && inviteInput) {
        copyButton.addEventListener("click", async () => {
            try {
                await navigator.clipboard.writeText(inviteInput.value);
                copyButton.textContent = "تم نسخ الرابط";
                if (feedback) {
                    feedback.textContent = "تقدرين الحين تشاركين الرابط.";
                }
            } catch (error) {
                inviteInput.focus();
                inviteInput.select();
                copyButton.textContent = "حددي الرابط وانسخيه";
                if (feedback) {
                    feedback.textContent = "انسخي الرابط المحدد باستخدام Ctrl + C.";
                }
            }
        });
    }
});
