document.addEventListener("DOMContentLoaded", function () {

    // Disable right click
    document.addEventListener("contextmenu", e => e.preventDefault());

    // Disable copy
    document.addEventListener("copy", e => e.preventDefault());

    // Disable cut
    document.addEventListener("cut", e => e.preventDefault());

    // Disable inspect shortcuts
    document.addEventListener("keydown", function (e) {

        if (
            e.key === "F12" ||
            (e.ctrlKey && e.shiftKey && ["I", "J", "C"].includes(e.key)) ||
            (e.ctrlKey && e.key === "u")
        ) {
            e.preventDefault();
        }
    });

    // Fullscreen
    const examShell = document.documentElement;

    if (examShell.requestFullscreen) {
        examShell.requestFullscreen();
    }

    // Timer
    const timerElement = document.getElementById("cbt-timer");

    if (timerElement) {

        let remainingSeconds = parseInt(
            timerElement.dataset.remaining
        );

        const countdown = setInterval(function () {

            const hours = Math.floor(remainingSeconds / 3600);
            const minutes = Math.floor((remainingSeconds % 3600) / 60);
            const seconds = remainingSeconds % 60;

            timerElement.innerHTML =
                `${hours.toString().padStart(2, "0")}:` +
                `${minutes.toString().padStart(2, "0")}:` +
                `${seconds.toString().padStart(2, "0")}`;

            if (remainingSeconds <= 300) {
                timerElement.style.color = "#ef4444";
            }

            if (remainingSeconds <= 0) {

                clearInterval(countdown);

                const autoSubmitForm = document.getElementById("cbt-submit-form");

                if (autoSubmitForm) {
                    autoSubmitForm.submit();
                }
            }

            remainingSeconds--;

        }, 1000);
    }

    // Option selection UI
    const options = document.querySelectorAll(".cbt-option");

    options.forEach(option => {

        option.addEventListener("click", function () {

            options.forEach(opt => {
                opt.classList.remove("selected");
            });

            option.classList.add("selected");

            const radio = option.querySelector("input[type=radio]");

            if (radio) {
                radio.checked = true;
            }
        });
    });

});