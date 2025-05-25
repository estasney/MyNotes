import "./styles/style.scss"

function addHeaderListener() {
    const header = document.querySelector(".header-radial");
    if (header) {
        header.addEventListener("click", () => {
            window.location.href = process.env.MAIN_PAGE;
        })
    }
}


(function () {
    if (document.readyState === "complete" || document.readyState === "interactive") {
        setTimeout(addHeaderListener, 10);
    } else {
        document.addEventListener("DOMContentLoaded", addHeaderListener)
    }
})();

