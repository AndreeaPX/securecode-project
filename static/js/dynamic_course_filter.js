document.addEventListener("DOMContentLoaded", function () {
    const yearInput = document.getElementById("id_year");
    const specializationSelect = document.getElementById("id_specialization");
    const coursesSelect = document.getElementById("id_courses");

    function fetchCourses() {
        const year = yearInput.value;
        const specialization = specializationSelect.value;

        if (!year || !specialization) return;

        fetch(`/admin/users/studentprofile/fetch-courses/?year=${year}&specialization=${specialization}`)
            .then(response => response.json())
            .then(data => {
                coursesSelect.innerHTML = "";
                data.forEach(course => {
                    const option = document.createElement("option");
                    option.value = course.id;
                    option.text = course.name;
                    coursesSelect.appendChild(option);
                });
            });
    }

    yearInput.addEventListener("change", fetchCourses);
    specializationSelect.addEventListener("change", fetchCourses);
});
