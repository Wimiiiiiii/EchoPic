// Importation des modules Firebase
import { initializeApp } from "https://www.gstatic.com/firebasejs/11.8.1/firebase-app.js";
import { getAuth, onAuthStateChanged, signInWithPopup, GoogleAuthProvider, signInWithEmailAndPassword, createUserWithEmailAndPassword, sendPasswordResetEmail, signOut } from "https://www.gstatic.com/firebasejs/11.8.1/firebase-auth.js";

// Configuration Firebase
const firebaseConfig = {
    apiKey: "AIzaSyDLLUxHFTuN73015L2cR6m6pYtdVKICbp8",
    authDomain: "echopic-b679d.firebaseapp.com",
    projectId: "echopic-b679d",
    storageBucket: "echopic-b679d.firebasestorage.app",
    messagingSenderId: "1003205566040",
    appId: "1:1003205566040:web:61b5cee410aa7dd0c3f42d",
    measurementId: "G-X0F64N3GC7"
};

// Initialisation Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

// Écouteur d'état d'authentification
onAuthStateChanged(auth, user => {
    if (user) {
        showSearchInterface();
    } else {
        showAuthOptions();
    }
});

// Fonctions de navigation entre les différents formulaires
window.showEmailAuth = function() {
    document.getElementById('auth-container').classList.add('hidden');
    document.getElementById('email-login-container').classList.remove('hidden');
    document.getElementById('register-container').classList.add('hidden');
    document.getElementById('forgot-password-container').classList.add('hidden');
}

window.showAuthOptions = function() {
    document.getElementById('auth-container').classList.remove('hidden');
    document.getElementById('email-login-container').classList.add('hidden');
    document.getElementById('register-container').classList.add('hidden');
    document.getElementById('forgot-password-container').classList.add('hidden');
}

window.showRegister = function() {
    document.getElementById('email-login-container').classList.add('hidden');
    document.getElementById('register-container').classList.remove('hidden');
}

window.showForgotPassword = function() {
    document.getElementById('email-login-container').classList.add('hidden');
    document.getElementById('forgot-password-container').classList.remove('hidden');
}

window.showSearchInterface = function() {
    hideAllContainers();
    document.getElementById('search-container').classList.remove('hidden');
}

function hideAllContainers() {
    const containers = [
        'auth-container',
        'email-login-container',
        'register-container',
        'forgot-password-container',
        'search-container'
    ];
    containers.forEach(id => {
        document.getElementById(id)?.classList.add('hidden');
    });
}

// Fonctions d'authentification
window.loginWithGoogle = function() {
    const provider = new GoogleAuthProvider();
    signInWithPopup(auth, provider)
        .then(() => showMessage("Connexion réussie!", "success"))
        .catch(error => {
            if (error.code !== 'auth/popup-closed-by-user') {
                showMessage("Erreur: " + error.message, "error");
                console.error(error);
            }
        });
}

window.loginWithEmail = function() {
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    
    if (!email || !password) {
        showMessage("Veuillez remplir tous les champs", "error");
        return;
    }

    signInWithEmailAndPassword(auth, email, password)
        .then(() => showMessage("Connexion réussie!", "success"))
        .catch(error => {
            showMessage("Erreur: " + error.message, "error");
            console.error(error);
        });
}

window.registerWithEmail = function() {
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    const confirmPassword = document.getElementById('register-confirm-password').value;
    
    if (!email || !password || !confirmPassword) {
        showMessage("Veuillez remplir tous les champs", "error");
        return;
    }

    if (password !== confirmPassword) {
        showMessage("Les mots de passe ne correspondent pas", "error");
        return;
    }
    
    if (password.length < 6) {
        showMessage("Le mot de passe doit contenir au moins 6 caractères", "error");
        return;
    }

    createUserWithEmailAndPassword(auth, email, password)
        .then(() => showMessage("Inscription réussie! Vous êtes maintenant connecté.", "success"))
        .catch(error => {
            showMessage("Erreur: " + error.message, "error");
            console.error(error);
        });
}

window.sendPasswordResetEmail = function() {
    const email = document.getElementById('reset-email').value;
    
    if (!email) {
        showMessage("Veuillez entrer votre email", "error");
        return;
    }

    sendPasswordResetEmail(auth, email)
        .then(() => showMessage("Email de réinitialisation envoyé!", "success"))
        .catch(error => {
            showMessage("Erreur: " + error.message, "error");
            console.error(error);
        });
}

window.logout = function() {
    signOut(auth)
        .then(() => {
            showAuthOptions();
            showMessage("Déconnexion réussie", "success");
        })
        .catch(error => {
            showMessage("Erreur lors de la déconnexion", "error");
            console.error(error);
        });
}

// Fonction utilitaire pour afficher les messages
window.showMessage = function(message, type = 'success') {
    const messageElement = document.getElementById('auth-message');
    messageElement.textContent = message;
    messageElement.className = `mt-4 p-3 rounded-md ${type === 'error' ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`;
    messageElement.classList.remove('hidden');
    
    setTimeout(() => {
        messageElement.classList.add('hidden');
    }, 5000);
}

// Gestion du drag & drop pour l'upload d'images
document.addEventListener('DOMContentLoaded', function() {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('image-upload');
    const preview = document.getElementById('preview');

    if (dropZone && fileInput && preview) {
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('border-indigo-500');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('border-indigo-500');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('border-indigo-500');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleFile(files[0]);
            }
        });

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleFile(e.target.files[0]);
            }
        });
    }
});

function handleFile(file) {
    if (!file.type.startsWith('image/')) {
        showMessage('Veuillez sélectionner une image valide', 'error');
        return;
    }

    const preview = document.getElementById('preview');
    const reader = new FileReader();

    reader.onload = (e) => {
        preview.src = e.target.result;
        preview.classList.remove('hidden');
    };

    reader.readAsDataURL(file);
}
