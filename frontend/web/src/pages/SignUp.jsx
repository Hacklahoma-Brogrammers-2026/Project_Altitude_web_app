import { Link, useNavigate } from 'react-router-dom'

const heroImage =
  'https://www.figma.com/api/mcp/asset/1959cab6-7ed8-4936-bc2d-d8d77e028471'

function SignUp() {
  const navigate = useNavigate()

  const handleSubmit = (event) => {
    event.preventDefault()
    navigate('/home')
  }

  return (
    <div className="login">
      <div className="login__bg" aria-hidden="true">
        <img src={heroImage} alt="" />
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
