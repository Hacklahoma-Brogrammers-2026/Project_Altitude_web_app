import { Link, useLocation, useNavigate } from 'react-router-dom'
import { HERO_IMAGE } from '../utils/constants'

function Login() {
  const navigate = useNavigate()
  const location = useLocation()
  const redirectPath = location.state?.from?.pathname ?? '/home'

  const handleSubmit = async (event) => {
    event.preventDefault()
    
    const formData = new FormData(event.target);
    const data = Object.fromEntries(formData.entries());

    try {
      const response = await fetch("http://localhost:8000/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
      });

      if (response.ok) {
        const result = await response.json();
        const userName = result?.username ?? data?.email?.split('@')[0] ?? ''
        localStorage.setItem(
          'altitudeUser',
          JSON.stringify({
            id: result?.user_id ?? null,
            username: userName,
            email: result?.email ?? data?.email ?? '',
          }),
        )
        console.log("Login successful:", result);
        navigate(redirectPath, { replace: true });
      } else {
        alert("Login failed");
      }
    } catch (error) {
       console.error("Error logging in:", error);
       alert("Error logging in");
    }
  }

  return (
    <div className="login">
      <div className="login__bg" aria-hidden="true">
        <img src={HERO_IMAGE} alt="" />
      </div>

      <main className="login__content">
        <h1 className="login__title">Altitude</h1>

        <section className="login__card" aria-label="Log in">
          <h2 className="login__card-title">Welcome Back</h2>

          <form className="login__form" onSubmit={handleSubmit}>
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
              autoComplete="current-password"
            />

            <button className="login__button" type="submit">
              Log In
            </button>
          </form>

          <p className="login__helper">
            Don’t have an account?{' '}
            <Link className="login__link" to="/signup">
              Sign up
            </Link>
          </p>
        </section>
      </main>
    </div>
  )
}

export default Login
