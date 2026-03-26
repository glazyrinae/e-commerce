document.addEventListener("DOMContentLoaded", () => {
    const cnt = document.querySelector(".cnt-good");
    const loadBtnMinus = document.querySelector(".btn-minus");
    const loadBtnPlus = document.querySelector(".btn-plus");

    if (!cnt) return;

    const minusGood = () => {
        const currentValue = Number.parseInt(cnt.value, 10) || 0;
        if (currentValue > 0) {
            cnt.value = String(currentValue - 1);
        }
    };

    const plusGood = () => {
        const currentValue = Number.parseInt(cnt.value, 10) || 0;
        cnt.value = String(currentValue + 1);
    };

    if (loadBtnMinus) {
        loadBtnMinus.addEventListener("click", minusGood);
    }

    if (loadBtnPlus) {
        loadBtnPlus.addEventListener("click", plusGood);
    }
});
