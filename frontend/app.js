
const flashcard = document.querySelector("#flashcard");
const forgotButton = document.querySelector("#forgot");
const rememberedButton = document.querySelector("#remembered");
const question = document.querySelector("#question");
const answer = document.querySelector("#answer");
const cardCounter = document.querySelector("#card-counter");

// Временная колода для проверки интерфейса.
const cards = [
    { question: "Aprovechar", answer: "Пользоваться, извлекать пользу" },
    { question: "Desarrollar", answer: "Развивать" },
    { question: "Lograr", answer: "Добиваться, достигать" },
];

// Прогресс текущей сессии хранится в памяти браузера.
let currentIndex = 0;
const forgottenCards = [];
let isAnimating = false;

// Отображаем текущую карточку и сбрасываем её состояние.
function renderCard() {
    const card = cards[currentIndex];

    question.textContent = card.question;
    answer.textContent = card.answer;
    cardCounter.textContent =
        `Карточка ${currentIndex + 1} из ${cards.length}`;

    flashcard.classList.remove(
        "is-flipped",
        "is-swiping-left",
        "is-swiping-right",
    );

    forgotButton.classList.remove("is-selected");
    rememberedButton.classList.remove("is-selected");
    forgotButton.disabled = false;
    rememberedButton.disabled = false;
    isAnimating = false;
}

// Переворачиваем карточку при клике на неё.
flashcard.addEventListener("click", () => {
    if (isAnimating) {
        return;
    }

    flashcard.classList.toggle("is-flipped");
});

// Фиксируем оценку, подсвечиваем кнопку и запускаем уход.
function submitAnswer(remembered) {
    if (isAnimating) {
        return;
    }

    isAnimating = true;

    if (!remembered) {
        forgottenCards.push(cards[currentIndex]);
        forgotButton.classList.add("is-selected");
    } else {
        rememberedButton.classList.add("is-selected");
    }

    forgotButton.disabled = true;
    rememberedButton.disabled = true;

    const direction = remembered
        ? "is-swiping-right"
        : "is-swiping-left";

    // Сначала показываем выбранную оценку, затем двигаем карточку.
    requestAnimationFrame(() => {
        flashcard.classList.add(direction);
    });
}

// После окончания движения показываем следующую карточку.
flashcard.addEventListener("transitionend", (event) => {
    if (event.propertyName !== "transform" || !isAnimating) {
        return;
    }

    currentIndex += 1;

    if (currentIndex < cards.length) {
        renderCard();
        return;
    }

    // Завершаем первый проход колоды.
    question.textContent = "Колода пройдена!";
    answer.textContent =
        `На повторение: ${forgottenCards.length} карточек`;
    cardCounter.textContent = "Сессия завершена";

    flashcard.classList.remove(
        "is-flipped",
        "is-swiping-left",
        "is-swiping-right",
    );

    isAnimating = false;
});

// Крестик: слово отправляется на повторение.
forgotButton.addEventListener("click", () => {
    submitAnswer(false);
});

// Галочка: слово считается запомненным.
rememberedButton.addEventListener("click", () => {
    submitAnswer(true);
});

// Показываем первую карточку.
renderCard();
