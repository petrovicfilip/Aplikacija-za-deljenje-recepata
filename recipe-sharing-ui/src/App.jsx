import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import ProfilePage from "./ProfilePage";
import RecipePage from "./RecipePage";

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
