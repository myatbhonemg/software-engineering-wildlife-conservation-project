// ===== REPORT SIGHTING JS =====

// Sign out function
function signOut() {
    localStorage.removeItem('user');
    window.location.href = '/logout';
}

// Toggle sidebar
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (sidebar) sidebar.classList.toggle('collapsed');
}

// ===== SET MAX DATE TO TODAY =====
document.addEventListener('DOMContentLoaded', function() {
    const dateInput = document.getElementById('date');
    const today = new Date().toISOString().split('T')[0];
    dateInput.setAttribute('max', today);
});

// ===== PHOTO UPLOAD =====
let uploadedPhotos = [];

function handlePhotoUpload(event) {
    const files = event.target.files;
    const previewContainer = document.getElementById('photo-preview');
    
    Array.from(files).forEach((file) => {
        if (file.size > 5 * 1024 * 1024) {
            alert('File ' + file.name + ' is too large. Max 5MB.');
            return;
        }
        if (!file.type.startsWith('image/')) {
            alert('File ' + file.name + ' is not an image.');
            return;
        }
        uploadedPhotos.push(file);
        const reader = new FileReader();
        reader.onload = function(e) {
            const previewItem = document.createElement('div');
            previewItem.className = 'preview-item';
            previewItem.innerHTML = `
                <img src="${e.target.result}" alt="Preview">
                <button type="button" class="remove-photo" onclick="removePhoto(${uploadedPhotos.length - 1})">×</button>
            `;
            previewContainer.appendChild(previewItem);
        };
        reader.readAsDataURL(file);
    });
    event.target.value = '';
}

function removePhoto(index) {
    uploadedPhotos.splice(index, 1);
    const previewContainer = document.getElementById('photo-preview');
    previewContainer.innerHTML = '';
    uploadedPhotos.forEach((file, i) => {
        const reader = new FileReader();
        reader.onload = function(e) {
            const previewItem = document.createElement('div');
            previewItem.className = 'preview-item';
            previewItem.innerHTML = `
                <img src="${e.target.result}" alt="Preview">
                <button type="button" class="remove-photo" onclick="removePhoto(${i})">×</button>
            `;
            previewContainer.appendChild(previewItem);
        };
        reader.readAsDataURL(file);
    });
}

// ===== CHARACTER COUNT =====
const descriptionInput = document.getElementById('description');
const charCountSpan = document.getElementById('char-count');

if (descriptionInput) {
    descriptionInput.addEventListener('input', function() {
        const length = this.value.length;
        charCountSpan.textContent = length;
        if (length > 450) charCountSpan.style.color = '#D64545';
        else if (length > 400) charCountSpan.style.color = '#E17B3C';
        else charCountSpan.style.color = 'var(--text-muted)';
        if (length > 500) {
            this.value = this.value.substring(0, 500);
            charCountSpan.textContent = '500';
        }
    });
}

// ===== FORM SUBMISSION =====
function handleSubmit(event) {
    event.preventDefault();

    const formData = new FormData();
    formData.append('species_id', document.getElementById('species').value);
    formData.append('count', document.getElementById('count').value);
    formData.append('location', document.getElementById('location').value);
    formData.append('region', document.getElementById('region').value);
    formData.append('date', document.getElementById('date').value);
    formData.append('time', document.getElementById('time').value);
    formData.append('description', document.getElementById('description').value);
    formData.append('condition', document.getElementById('habitat').value);

    // appending uploaded photos
    // A sighting can have multiple photos
    uploadedPhotos.forEach((photo, i) => {
        formData.append('photos', photo);
    });

    fetch('/submit-sighting', {
        method: 'POST',
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            document.getElementById('sighting-form').style.display = 'none';
            document.getElementById('success-message').style.display = 'block';
            window.scrollTo({ top: 0, behavior: 'smooth' });
        } else {
            alert('Error: ' + (data.message || 'Failed to submit report'));
        }
    })
    .catch(() => alert('Server error. Please try again.'));
}


// ===== RESET FORM =====
function resetForm() {
    document.getElementById('sighting-form').reset();
    uploadedPhotos = [];
    document.getElementById('photo-preview').innerHTML = '';
    if (charCountSpan) charCountSpan.textContent = '0';
    document.getElementById('success-message').style.display = 'none';
    document.getElementById('sighting-form').style.display = 'block';
    window.scrollTo({ top: 0, behavior: 'smooth' });
}