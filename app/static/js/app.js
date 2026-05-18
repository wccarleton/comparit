const state = {
  pair: null,
  loading: false,
  pairLoadedAt: null,
  browserSessionId: getBrowserSessionId(),
  token: document.querySelector(".intro")?.dataset.token || "",
  accessGranted: document.querySelector(".intro")?.dataset.accessGranted === "true",
  consentRequired: document.querySelector(".intro")?.dataset.consentRequired === "true",
  completionText: document.querySelector(".intro")?.dataset.completionText || "",
  tokenExpiredText: document.querySelector(".intro")?.dataset.tokenExpiredText || "",
};

const splashPanel = document.querySelector("#splash-panel");
const comparisonPanel = document.querySelector("#comparison-panel");
const finishPanel = document.querySelector("#finish-panel");
const finishTitle = document.querySelector("#finish-title");
const finishMessage = document.querySelector("#finish-message");
const consentCheckbox = document.querySelector("#consent-checkbox");
const acceptConsentButton = document.querySelector("#accept-consent-button");
const statusElement = document.querySelector("#comparison-status");
const selectorElement = document.querySelector("#selector-name");
const skipButton = document.querySelector("#skip-pair-button");
const tieButton = document.querySelector("#tie-pair-button");
const choiceButtons = Array.from(document.querySelectorAll(".image-choice"));

function getBrowserSessionId() {
  const storageKey = "comparit_browser_session_id";
  const existingId = window.localStorage.getItem(storageKey);
  if (existingId) {
    return existingId;
  }

  const newId = window.crypto.randomUUID();
  window.localStorage.setItem(storageKey, newId);
  return newId;
}

function setStatus(message) {
  if (statusElement) {
    statusElement.textContent = message;
  }
}

function setChoicesEnabled(enabled) {
  choiceButtons.forEach((button) => {
    button.disabled = !enabled;
  });
}

function showComparisonPanel() {
  if (splashPanel) {
    splashPanel.hidden = true;
  }
  if (comparisonPanel) {
    comparisonPanel.hidden = false;
  }
  if (finishPanel) {
    finishPanel.hidden = true;
  }
}

function showFinishPanel(title, message) {
  if (splashPanel) {
    splashPanel.hidden = true;
  }
  if (comparisonPanel) {
    comparisonPanel.hidden = true;
  }
  if (finishTitle) {
    finishTitle.textContent = title;
  }
  if (finishMessage) {
    finishMessage.textContent = message;
  }
  if (finishPanel) {
    finishPanel.hidden = false;
  }
}

function imageForSide(pair, side) {
  return side === "left" ? pair.left : pair.right;
}

function renderPair(pair) {
  if (pair.completed) {
    renderCompletion();
    return;
  }

  if (pair.expired) {
    renderExpiry();
    return;
  }

  const leftImage = document.querySelector("#left-image");
  const rightImage = document.querySelector("#right-image");

  leftImage.src = pair.left.url;
  leftImage.alt = pair.left.label;
  rightImage.src = pair.right.url;
  rightImage.alt = pair.right.label;

  if (selectorElement) {
    selectorElement.textContent = pair.strategy;
  }

  state.pairLoadedAt = performance.now();
  setChoicesEnabled(true);
  setStatus("Select the image that best matches the instructions.");
}

function renderCompletion() {
  setChoicesEnabled(false);
  state.pair = null;
  showFinishPanel("Task complete", state.completionText);
}

function renderExpiry() {
  setChoicesEnabled(false);
  state.pair = null;
  showFinishPanel("Link expired", state.tokenExpiredText);
}

async function loadNextPair() {
  if (state.loading) {
    return;
  }

  state.loading = true;
  setChoicesEnabled(false);
  setStatus("Loading image pair...");

  try {
    const query = state.token ? `?token=${encodeURIComponent(state.token)}` : "";
    const response = await fetch(`/api/pair${query}`);
    if (!response.ok) {
      if (response.status === 403) {
        const errorResult = await response.json();
        if (errorResult.detail === "Participant token has expired.") {
          renderExpiry();
          return;
        }
      }
      throw new Error(`Could not load pair: ${response.status}`);
    }

    state.pair = await response.json();
    renderPair(state.pair);
  } catch (error) {
    console.error(error);
    setStatus("Could not load an image pair. Check the server logs and image config.");
  } finally {
    state.loading = false;
  }
}

function responseTimeMs() {
  if (!state.pairLoadedAt) {
    return 0;
  }
  return Math.round(performance.now() - state.pairLoadedAt);
}

async function submitResponse(action, side = null) {
  if (!state.pair || state.loading) {
    return;
  }

  const selectedImage = side ? imageForSide(state.pair, side) : null;
  state.loading = true;
  setChoicesEnabled(false);
  setStatus("Saving response...");

  try {
    const response = await fetch("/api/choices", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        browser_session_id: state.browserSessionId,
        token: state.token || null,
        action,
        selected_image_id: selectedImage ? selectedImage.id : null,
        left_image_id: state.pair.left.id,
        right_image_id: state.pair.right.id,
        strategy: state.pair.strategy,
        response_time_ms: responseTimeMs(),
      }),
    });

    if (!response.ok) {
      if (response.status === 403) {
        const errorResult = await response.json();
        if (errorResult.detail === "Participant token has expired.") {
          state.loading = false;
          renderExpiry();
          return;
        }
      }
      throw new Error(`Could not save response: ${response.status}`);
    }

    const result = await response.json();
    state.loading = false;
    if (result.completed) {
      renderCompletion();
      return;
    }
    await loadNextPair();
  } catch (error) {
    console.error(error);
    state.loading = false;
    setChoicesEnabled(true);
    setStatus("Could not save that response. Try again or check the server logs.");
  }
}

choiceButtons.forEach((button) => {
  button.addEventListener("click", () => {
    submitResponse("select", button.dataset.side);
  });
});

if (skipButton) {
  skipButton.addEventListener("click", () => {
    submitResponse("skip");
  });
}

if (tieButton) {
  tieButton.addEventListener("click", () => {
    submitResponse("tie");
  });
}

if (consentCheckbox && acceptConsentButton) {
  consentCheckbox.addEventListener("change", () => {
    acceptConsentButton.disabled = !consentCheckbox.checked;
  });

  acceptConsentButton.addEventListener("click", async () => {
    acceptConsentButton.disabled = true;
    try {
      const response = await fetch("/api/consent", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          token: state.token || null,
        }),
      });

      if (!response.ok) {
        throw new Error(`Could not accept consent: ${response.status}`);
      }

      state.consentRequired = false;
      showComparisonPanel();
      await loadNextPair();
    } catch (error) {
      console.error(error);
      acceptConsentButton.disabled = false;
    }
  });
}

if (state.accessGranted && !state.consentRequired) {
  showComparisonPanel();
  loadNextPair();
}
