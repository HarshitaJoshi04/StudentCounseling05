
// dropdown show
const avatar = document.querySelector(".navbar-avatar");
const info = document.getElementById("dropdown-menu");

avatar.addEventListener("click", (e) => {
  e.stopPropagation(); // Prevent window click from hiding it immediately
  // Toggle class for smooth show/hide
  info.classList.toggle("show");
});

// Hide when clicking outside
window.addEventListener("click", () => {
  info.classList.remove("show");
});




//personal info modal

  function openInfoModal() {
    document.getElementById("infoModal").style.display = "block";
  }

  function closeInfoModal() {
    document.getElementById("infoModal").style.display = "none";
  }

  // Optional: click outside to close
  window.addEventListener("click", function(event) {
    const modal = document.getElementById("infoModal");
    if (event.target === modal) {
      modal.style.display = "none";
    }
  });






document.addEventListener("DOMContentLoaded", function () {
  const btn = document.getElementById("toggleFormBtn");
  const modal = document.getElementById("formModal");
  const closebtn = document.querySelector(".closebtn");

  // Open when dashboard "Fill Form" button is clicked
  if (btn) {
    btn.addEventListener("click", () => {
      modal.style.display = "block";
    });
  }

  // Open when card "Open" button is clicked
  window.openFormModal = function () {
    modal.style.display = "block";
  };

  // Close on ❌
  if (closebtn) {
    closebtn.addEventListener("click", () => {
      modal.style.display = "none";
    });
  }

  // Close if clicked outside the modal content
  window.addEventListener("click", (e) => {
    if (e.target === modal) {
      modal.style.display = "none";
    }
  });
});




// fee modal
function openFeeModal() {
  const modal = document.getElementById("feeModal");
  if (modal) modal.style.display = "block";
}

function closeFeeModal() {
  const modal = document.getElementById("feeModal");
  if (modal) modal.style.display = "none";
}

window.addEventListener("click", function (e) {
  const modal = document.getElementById("feeModal");
  if (e.target === modal) {
    modal.style.display = "none";
  }
});


// student help modal

function openHelpModal() {
  document.getElementById("helpModal").style.display = "block";
}

function closeHelpModal() {
  document.getElementById("helpModal").style.display = "none";
}


// admin modal
function openAdminHelpModal() {
  document.getElementById("adminHelpModal").style.display = "block";
}

function closeAdminHelpModal() {
  document.getElementById("adminHelpModal").style.display = "none";
}


// hamburger

