document.addEventListener("DOMContentLoaded", function () {
    const yearInput = document.getElementById("id_year");
    const specializationSelect = document.getElementById("id_specialization");
    const coursesSelect = document.getElementById("id_courses");

    if(!(yearInput && specializationSelect && coursesSelect)){
        return;
    }

    function fetchCourses() {
        const year = yearInput.value;
        const specialization = specializationSelect.value;

        if (!year || !specialization) {
            return;
        }

        coursesSelect.innerHTML = "<option disabled selected>Loading courses...</option>";

        fetch(`/admin/users/studentprofile/fetch-courses/?year=${year}&specialization=${specialization}`)
            .then(response =>{
                if(!response.ok) throw new Error ("Network respons is not ok.");
                return response.json();
            })
            .then(data => {
                const selectedValues = Array.from(coursesSelect.selectedOptions).map(opt => opt.value);
                coursesSelect.innerHTML = "";
                if(data.lenght === 0){
                    const option = document.createElement("option");
                    option.disabled = true;
                    option.text = "No courses found!";
                    coursesSelect.appendChild(option);
                    return;
                }
                data.forEach(course => {
                    const option = document.createElement("option");
                    option.value = course.id;
                    option.text = course.name;
                    if(selectedValues.includes(String(course.id))){
                        option.selected = true;
                    }
                    coursesSelect.appendChild(option);
                });
            }).catch(error=>{
                    console.error("Error fetching courses ", error);
                    coursesSelect.innerHTML = "";
                    const option = document.createElement("option");
                    option.disabled = true;
                    option.text = "Error loading courses...";
                    coursesSelect.appendChild(option);

            });
    }

    yearInput.addEventListener("change", fetchCourses);
    specializationSelect.addEventListener("change", fetchCourses);
});
