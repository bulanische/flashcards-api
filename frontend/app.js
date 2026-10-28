const flashcard = document.querySelector("#flashcard");
const forgotButton = document.querySelector("#forgot");
const rememberedButton = document.querySelector("#remembered");
const question = document.querySelector("#question");
const answer = document.querySelector("#answer");
const cardCounter = document.querySelector("#card-counter");
const authSection = document.querySelector("#auth");
const loginForm = document.querySelector("#login-form");
const authError = document.querySelector("#auth-error");
const userPanel = document.querySelector("#user-panel");
const logoutButton = document.querySelector("#logout");
const deckSelection = document.querySelector("#deck-selection");
const reviewSection = document.querySelector("#review");
const deckSelect = document.querySelector("#deck-select");
const startReviewButton = document.querySelector("#start-review");

// Загружаем колоды текущего пользователя.
async function loadDecks() {
    deckSelect.replaceChildren();
    startReviewButton.disabled = true;

    try {
        const response = await fetch("/decks/", {
            headers: {
                Authorization: `Bearer ${accessToken}`,
            },
        });

        if (!response.ok) {
            throw new Error("Не удалось загрузить колоды.");
        }

        const decks = await response.json();

        if (decks.length === 0) {
            deckSelect.add(new Option("Нет доступных колод", ""));
            return;
        }

        deckSelect.add(new Option("Выберите колоду", ""));

        decks.forEach((deck) => {
            deckSelect.add(new Option(deck.name, deck.id));
        });

        startReviewButton.disabled = false;
    } catch (error) {
        deckSelect.add(new Option("Ошибка загрузки колод", ""));
        console.error(error);
    }
}

// Показываем нужные блоки в зависимости от авторизации.
function setAuthenticatedUI(isAuthenticated) {
    authSection.hidden = isAuthenticated;
    userPanel.hidden = !isAuthenticated;
    deckSelection.hidden = !isAuthenticated;
    reviewSection.hidden = !isAuthenticated;
}

// Храним access-токен только в памяти текущей страницы.
let accessToken = null;

// Отправляем данные формы на API для входа.
loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    authError.textContent = "";

    const formData = new FormData(loginForm);
    const credentials = new URLSearchParams(formData);

    try {
        const response = await fetch("/auth/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
            },
            body: credentials,
            credentials: "include",
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error("Неверный email или пароль.");
        }

        accessToken = data.access_token;

        setAuthenticatedUI(true);
        await loadDecks();
    } catch (error) {
        authError.textContent =
            error.message || "Не удалось выполнить вход.";
    }
});

// Завершаем сессию на сервере и возвращаем форму входа.
logoutButton.addEventListener("click", async () => {
    try {
        const response = await fetch("/auth/logout", {
            method: "POST",
            credentials: "include",
        });

        if (!response.ok) {
            throw new Error("Не удалось завершить сессию.");
        }

        accessToken = null;
        setAuthenticatedUI(false);
        loginForm.reset();
        authError.textContent = "";
    } catch (error) {
        authError.textContent =
            error.message || "Ошибка при выходе.";
    }
});

// Восстанавливаем авторизацию по refresh-cookie.
async function restoreSession() {
    try {
        const response = await fetch("/auth/refresh", {
            method: "POST",
            credentials: "include",
        });

        if (!response.ok) {
            return;
        }

        const data = await response.json();
        accessToken = data.access_token;

        setAuthenticatedUI(true);
        await loadDecks();
    } catch (error) {
        console.error("Не удалось восстановить сессию:", error);
    }
}

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

// Проверяем сохранённую сессию после загрузки страницы.
restoreSession();