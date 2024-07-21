const startTime = new Date("{{ test.start_date }}");
const endTime = new Date("{{ test.end_date }}");
const currentTime = new Date();
const remainingTime = endTime - currentTime;
  
const timerElement = document.getElementById("timer");
const form = document.getElementById("test-form");

    let timeoutId = setTimeout(() => {
        form.submit(); // Submit the form when time runs out
    }, remainingTime);

    let intervalId = setInterval(() => {
        const timeLeft = Math.max(0, remainingTime - (new Date() - startTime));
        const minutes = Math.floor(timeLeft / 60000);
        const seconds = Math.floor((timeLeft % 60000) / 1000);
        timerElement.textContent = `${minutes} minutes ${seconds} seconds`;

        if (timeLeft <= 0) {
            clearTimeout(timeoutId);
            clearInterval(intervalId);
            form.submit(); // Submit the form when time runs out
        }
    }, 1000);