const cards = [...document.querySelectorAll(".profile-card")];
const currentCounter = document.querySelector(".counter-current");
const gestureHint = document.querySelector(".gesture-hint");

let order = [...cards];
let activeCard = null;
let pointerId = null;
let startX = 0;
let startY = 0;
let dragX = 0;
let dragY = 0;
let lastX = 0;
let lastTime = 0;
let velocityX = 0;
let isAnimating = false;
let interactionCount = 0;

const baseRotations = [0, 4.5, -5, 7.5, -8.5];
const baseX = [0, 17, -18, 29, -30];
const baseY = [0, 7, 13, 20, 27];

function displayNumber(card) {
  return card.querySelector(".card-number").textContent.slice(0, 2);
}

function renderStack(immediate = false) {
  order.forEach((card, index) => {
    card.style.zIndex = String(order.length - index);
    card.style.pointerEvents = index === 0 && !isAnimating ? "auto" : "none";
    card.setAttribute("aria-hidden", index === 0 ? "false" : "true");
    card.tabIndex = index === 0 ? 0 : -1;

    if (card === activeCard) return;

    gsap.to(card, {
      duration: immediate ? 0 : 0.62,
      ease: "power3.out",
      rotation: baseRotations[index],
      scale: 1 - index * 0.022,
      x: baseX[index],
      y: baseY[index],
    });
  });

  currentCounter.textContent = displayNumber(order[0]);
}

function setBackCardsProgress(progress, direction) {
  order.slice(1).forEach((card, offset) => {
    const index = offset + 1;
    const promotedIndex = Math.max(index - progress, 0);
    const nextRotation = gsap.utils.interpolate(
      baseRotations[index],
      baseRotations[Math.max(index - 1, 0)],
      progress,
    );
    const sideways = index === 1 ? direction * progress * 7 : 0;

    gsap.to(card, {
      duration: 0.16,
      ease: "power2.out",
      rotation: nextRotation,
      scale: 1 - promotedIndex * 0.022,
      x: gsap.utils.interpolate(baseX[index], baseX[Math.max(index - 1, 0)], progress) + sideways,
      y: gsap.utils.interpolate(baseY[index], baseY[Math.max(index - 1, 0)], progress),
    });
  });
}

function onPointerDown(event) {
  if (isAnimating || event.currentTarget !== order[0]) return;

  activeCard = event.currentTarget;
  pointerId = event.pointerId;
  startX = lastX = event.clientX;
  startY = event.clientY;
  lastTime = performance.now();
  velocityX = 0;
  dragX = dragY = 0;

  activeCard.setPointerCapture(pointerId);
  activeCard.classList.add("is-dragging");
  gsap.killTweensOf(activeCard);
  gsap.to(activeCard, { duration: 0.18, ease: "power2.out", scale: 1.025 });

  if (interactionCount === 0) {
    gsap.to(gestureHint, { autoAlpha: 0, duration: 0.28, y: 8 });
  }
}

function onPointerMove(event) {
  if (!activeCard || event.pointerId !== pointerId) return;

  const now = performance.now();
  dragX = event.clientX - startX;
  dragY = event.clientY - startY;
  velocityX = (event.clientX - lastX) / Math.max(now - lastTime, 1);
  lastX = event.clientX;
  lastTime = now;

  const progress = Math.min(Math.abs(dragX) / 180, 1);
  const direction = dragX === 0 ? 0 : Math.sign(dragX);

  gsap.set(activeCard, {
    rotation: dragX * 0.055,
    scale: 1.025,
    x: dragX,
    y: dragY * 0.72,
  });
  setBackCardsProgress(progress, direction);
}

function releaseCard(event) {
  if (!activeCard || (event.pointerId !== undefined && event.pointerId !== pointerId)) return;

  const card = activeCard;
  const shouldAdvance = Math.abs(dragX) > 105 || Math.abs(velocityX) > 0.75;
  card.classList.remove("is-dragging");
  activeCard = null;
  pointerId = null;

  if (shouldAdvance) {
    const direction = Math.sign(dragX || velocityX || 1);
    advance(direction, card, dragY);
  } else {
    gsap.to(card, {
      duration: 0.7,
      ease: "elastic.out(1, 0.7)",
      rotation: baseRotations[0],
      scale: 1,
      x: baseX[0],
      y: baseY[0],
    });
    renderStack();
  }
}

function advance(direction = 1, card = order[0], yOffset = 0) {
  if (isAnimating) return;
  isAnimating = true;
  const shouldMoveFocus = document.activeElement === card;
  interactionCount += 1;
  order.forEach((item) => (item.style.pointerEvents = "none"));

  const currentX = Number(gsap.getProperty(card, "x")) || 0;
  const sideX = direction * Math.min(
    Math.max(Math.abs(currentX), card.offsetWidth * 0.42),
    card.offsetWidth * 0.62,
  );
  const sideY = gsap.utils.clamp(-20, 42, yOffset * 0.3 + 18);

  // Move the selected card just outside the stack, drop it behind the
  // remaining cards, then visibly tuck it into the last position.
  gsap.to(card, {
    duration: 0.26,
    ease: "power2.out",
    rotation: direction * 10,
    scale: 0.965,
    x: sideX,
    y: sideY,
    onComplete: () => {
      order.shift();
      order.push(card);

      order.forEach((item, index) => {
        item.style.zIndex = String(order.length - index);
        item.style.pointerEvents = index === 0 ? "auto" : "none";
        item.setAttribute("aria-hidden", index === 0 ? "false" : "true");
        item.tabIndex = index === 0 ? 0 : -1;
      });

      currentCounter.textContent = displayNumber(order[0]);

      order.slice(0, -1).forEach((item, index) => {
        gsap.to(item, {
          delay: index * 0.025,
          duration: 0.58,
          ease: "power3.out",
          rotation: baseRotations[index],
          scale: 1 - index * 0.022,
          x: baseX[index],
          y: baseY[index],
        });
      });

      gsap.to(card, {
        duration: 0.6,
        ease: "power3.inOut",
        rotation: baseRotations[order.length - 1],
        scale: 1 - (order.length - 1) * 0.022,
        x: baseX[order.length - 1],
        y: baseY[order.length - 1],
        onComplete: () => {
          isAnimating = false;
          if (shouldMoveFocus) order[0].focus({ preventScroll: true });
        },
      });
    },
  });
}

cards.forEach((card) => {
  card.addEventListener("pointerdown", onPointerDown);
  card.addEventListener("pointermove", onPointerMove);
  card.addEventListener("pointerup", releaseCard);
  card.addEventListener("pointercancel", releaseCard);
  card.addEventListener("lostpointercapture", releaseCard);
  card.addEventListener("keydown", (event) => {
    if (card !== order[0] || isAnimating) return;
    if (event.key === "ArrowRight" || event.key === "ArrowLeft") {
      event.preventDefault();
      advance(event.key === "ArrowRight" ? 1 : -1);
    }
  });
});

gsap.set(cards, { transformPerspective: 900, transformOrigin: "50% 108%" });
renderStack(true);

gsap.from(".topbar > *", {
  delay: 0.1,
  duration: 0.7,
  ease: "power3.out",
  opacity: 0,
  stagger: 0.08,
  y: -10,
});
gsap.from([".eyebrow", "h1", ".intro"], {
  delay: 0.18,
  duration: 0.85,
  ease: "power3.out",
  opacity: 0,
  stagger: 0.1,
  y: 24,
});
gsap.from(cards, {
  delay: 0.38,
  duration: 0.9,
  ease: "back.out(1.35)",
  opacity: 0,
  stagger: -0.07,
  y: 70,
});
gsap.to(".gesture-hint svg", {
  duration: 1.2,
  ease: "sine.inOut",
  repeat: -1,
  x: 8,
  yoyo: true,
});
