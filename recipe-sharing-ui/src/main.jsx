import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { CurrentUserProvider } from "./current_user/CurrentUserContext.jsx";

const DEFAULT_USER_ID = "fc184998-e09e-451b-925b-2f496f279b50";

createRoot(document.getElementById("root")).render(
    <StrictMode>
      <CurrentUserProvider defaultUserId={DEFAULT_USER_ID}>
        <App />
      </CurrentUserProvider>
    </StrictMode>
);