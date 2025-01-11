const randomContent = [
    "Content Generating...",
    "Calculating the meaning of life... (It's 42, by the way.)",
    "Just kidding, it's just loading.",
    "Counting down the seconds until your impatience grows... 5... 4... 3... 2... 1... Just kidding, it's still loading."
];

let lastIndex = -1; // To track the last index used

function changeText() {
    const loadingText = document.querySelector('.loading-text');
    let randomIndex;

    // Ensure the new random index is not the same as the last one
    do {
        randomIndex = Math.floor(Math.random() * randomContent.length);
    } while (randomIndex === lastIndex);

    lastIndex = randomIndex; // Update the last index

    // Fade out the current text
    loadingText.style.opacity = 0;
    setTimeout(() => {
        // Change the text after the fade-out completes
        loadingText.textContent = randomContent[randomIndex];

        // Fade in the new text
        loadingText.style.opacity = 1;
    }, 1000); // 1-second fade-out before changing text
}

// Adjust the interval to allow sufficient time for fade-in, display, and fade-out
setInterval(() => {
    changeText();
}, 5000); // Text changes every 5 seconds

setTimeout(() => {
    document.querySelector('.loading-container').style.display = 'none';
    document.querySelector('header').style.display = 'block';
    document.querySelector('main').style.display = 'block';
    document.querySelector('body').style.background = "linear-gradient(45deg, rgba(255, 255, 255, 0.195), rgba(135, 217, 237, 0.493))";
}, 60000);
db.collection('businessInfo').doc(companyName).onSnapshot((doc) => {
    if (doc.exists) {
        const data = doc.data();
        const visits = data.visits;
        console.log("Visits:", visits);

        if(visits > 1){
            document.querySelector('.loading-container').style.display = 'none';
            document.querySelector('header').style.display = 'block';
            document.querySelector('main').style.display = 'block';
            document.querySelector('body').style.background = "linear-gradient(45deg, rgba(255, 255, 255, 0.195), rgba(135, 217, 237, 0.493))";
        }
    }
})