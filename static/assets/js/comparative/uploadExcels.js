buttons = document.getElementsByClassName('reportingType');

buttons.forEach(button => {
    button.addEventListener("click", () => changeInputValue(button.id));
});

function changeInputValue(value) {
    document.getElementById('reportingType').value = value
    document.getElementById('buttonSubmit').disabled = false

    console.log(document.getElementById('reportingType'))
}