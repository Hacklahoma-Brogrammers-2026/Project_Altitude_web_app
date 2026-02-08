import { Link, useNavigate } from 'react-router-dom'
import { HERO_IMAGE } from '../utils/constants'

function SignUp() {
  const navigate = useNavigate()

  const handleSubmit = async (event) => {
    event.preventDefault()
    
    const formData = new FormData(event.target);
    const data = Object.fromEntries(formData.entries());

    // Backend expects 'username' but form has 'fullName'
    const payload = {
      username: data.fullName,
      email: data.email,
      password: data.password
    };


    try {
      const response = await fetch("http://192.168.137.1:8000/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        const result = await response.json();
        console.log("Registration successful:", result);
        // After sign up, redirect to login or home
        navigate('/login');
      } else {
         const errorData = await response.json();
         alert(`Registration failed: ${errorData.detail || 'Unknown error'}`);
      }
    } catch (error) {
       console.error("Error registering:", error);
       alert("Error registering");
    }
  }

  return (
    <div className="login">
      <div className="login__bg" aria-hidden="true">
        <img src={HERO_IMAGE} alt="" />
      </div>

      <main className="login__content">
        <h1 className="login__title">Altitude</h1>

        <section className="login__card" aria-label="Sign up">
          <h2 className="login__card-title">Create Account</h2>

          <form className="login__form" onSubmit={handleSubmit}>
            <label className="login__label" htmlFor="fullName">
              Full name
            </label>
            <input
              className="login__input"
              id="fullName"
              name="fullName"
              type="text"
              autoComplete="name"
            />

            <label className="login__label" htmlFor="email">
              Email
            </label>
            <input
              className="login__input"
              id="email"
              name="email"
              type="email"
              autoComplete="email"
            />

            <label className="login__label" htmlFor="password">
              Password
            </label>
            <input
              className="login__input"
              id="password"
              name="password"
              type="password"
              autoComplete="new-password"
            />

            <button className="login__button" type="submit">
              Sign Up
            </button>
          </form>

          <p className="login__helper">
            Already have an account?{' '}
            <Link className="login__link" to="/login">
              Log In
            </Link>
          </p>
        </section>
      </main>
    </div>
  )
}

export default SignUp
