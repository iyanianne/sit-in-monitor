function handleLogin(event) {
    event.preventDefault();
    
    const idno = document.getElementById('idno').value;
    const password = document.getElementById('password').value;

    // Add your login API call here
    fetch('/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            idno: idno,
            password: password
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.href = '/dashboard';  // Redirect to dashboard on success
        } else {
            alert('Login failed: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred during login');
    });
}

function handleRegister(event) {
    event.preventDefault();
    
    const formData = {
        idno: document.getElementById('idno').value,
        last_name: document.getElementById('last_name').value,
        first_name: document.getElementById('first_name').value,
        mid_name: document.getElementById('mid_name').value,
        course: document.getElementById('course').value,
        yr_lvl: document.getElementById('yr_lvl').value,
        email: document.getElementById('email').value,
        username: document.getElementById('username').value,
        password: document.getElementById('password').value
    };

    // Add your registration API call here
    fetch('/register', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.href = '/login';  // Redirect to login page on success
        } else {
            alert('Registration failed: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred during registration');
    });
}