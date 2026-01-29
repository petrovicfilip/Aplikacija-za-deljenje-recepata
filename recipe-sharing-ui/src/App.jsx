import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import ProfilePage from "./components/ProfilePage";
import RecipePage from "./components/RecipePage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/profile" replace />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/recipes/:id" element={<RecipePage />} />
      </Routes>
    </BrowserRouter>
  );
}
