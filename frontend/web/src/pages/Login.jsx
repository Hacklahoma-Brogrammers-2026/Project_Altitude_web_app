import { useNavigate } from 'react-router-dom'

const heroImage =
  'https://www.figma.com/api/mcp/asset/1959cab6-7ed8-4936-bc2d-d8d77e028471'

function Login() {
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

        <section className="login__card" aria-label="Log in">
          <h2 className="login__card-title">Welcome Back</h2>

          <form className="login__form" onSubmit={handleSubmit}>
            <label className="login__label" htmlFor="username">
              User
            </label>
            <input
              className="login__input"
              id="username"
              name="username"
              type="text"
              autoComplete="username"
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
        </section>
      </main>
    </div>
  )
}

export default Login
