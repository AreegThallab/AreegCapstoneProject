
document.addEventListener("DOMContentLoaded", () => {
    // =========================================
    // 01. CONFIRM PAYOUT DELIVERY
    // =========================================
    const deliveryForms = document.querySelectorAll(".delivery-confirm-form");

    deliveryForms.forEach((form) => {
        form.addEventListener("submit", (event) => {
            const button = form.querySelector(".delivery-confirm-btn");
            if (!button) return;

            const recipient = button.dataset.recipient || "صاحب الدور";
            const confirmed = window.confirm(
                `هل تؤكد أنك سلّمت مبلغ هذه الدورة إلى ${recipient} خارج منصة دَوْرة؟`
            );

            if (!confirmed) {
                event.preventDefault();
            } else {
                button.disabled = true;
                button.textContent = "جاري تسجيل التأكيد...";
            }
        });
    });
});
