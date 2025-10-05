document.addEventListener('DOMContentLoaded', function() {
    const userNickname = document.getElementById('user-nickname');
    const dropdownMenu = document.getElementById('dropdown-menu');

    userNickname.addEventListener('click', function(event) {
        event.preventDefault();
        if (dropdownMenu.style.display === "none" || !dropdownMenu.style.display) {
            dropdownMenu.style.display = "block";
        } else {
            dropdownMenu.style.display = "none";
        }
    });
});