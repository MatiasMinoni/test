document.addEventListener("DOMContentLoaded", () => {
    var element = document.getElementById('form').childNodes;

    element.forEach((item) => {
        if (item.name != 'login' && item.name != undefined) {

            item.addEventListener("input", () => {
                let label = document.getElementById(item.name + '-label')
                if (label != undefined && item.value.length != 0) {
                    label.style.opacity = 1;
                } else {
                    label.style.opacity = 0;
                };
            });
        };
    });
});