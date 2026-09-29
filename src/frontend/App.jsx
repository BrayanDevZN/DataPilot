import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "react-hot-toast";

import Login from "./pages/Login";
import Register from "./pages/Register";
import RegisterCode from "./pages/RegisterCode";
import ForgotPassword from "./pages/ForgotPassword";
import ForgotPasswordCode from "./pages/ForgotPasswordCode";
import ProfilePhotoSetup from "./pages/ProfilePhotoSetup";

import Home from "./pages/Home";
import Chat from "./pages/Chat";
import Settings from "./pages/Settings";
import SettingsRecoverPassword from "./pages/SettingsRecoverPassword";
import Dashboards from "./pages/Dashboards";
import Help from "./pages/Help";
import DataSources from "./pages/DataSources";
import Collaborations from "./pages/Collaborations";

import PrivateRoute from "./routes/PrivateRoute";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />

        <Route path="/register" element={<Register />} />
        <Route path="/register-code" element={<RegisterCode />} />

        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/forgot-password-code" element={<ForgotPasswordCode />} />

        <Route
          path="/profile-photo-setup"
          element={
            <PrivateRoute>
              <ProfilePhotoSetup />
            </PrivateRoute>
          }
        />

        <Route
          path="/home"
          element={
            <PrivateRoute>
              <Home />
            </PrivateRoute>
          }
        />

        <Route
          path="/dashboards"
          element={
            <PrivateRoute>
              <Dashboards />
            </PrivateRoute>
          }
        />

        <Route
          path="/data-sources"
          element={
            <PrivateRoute>
              <DataSources />
            </PrivateRoute>
          }
        />

        <Route
          path="/collaborations"
          element={
            <PrivateRoute>
              <Collaborations />
            </PrivateRoute>
          }
        />

        <Route
          path="/chat"
          element={
            <PrivateRoute>
              <Chat />
            </PrivateRoute>
          }
        />

        <Route
          path="/chat/:conversationId"
          element={
            <PrivateRoute>
              <Chat />
            </PrivateRoute>
          }
        />

        <Route
          path="/help"
          element={
            <PrivateRoute>
              <Help />
            </PrivateRoute>
          }
        />

        <Route
          path="/settings"
          element={
            <PrivateRoute>
              <Settings />
            </PrivateRoute>
          }
        />

        <Route
          path="/settings/recover-password"
          element={
            <PrivateRoute>
              <SettingsRecoverPassword />
            </PrivateRoute>
          }
        />

        <Route path="*" element={<Navigate to="/home" replace />} />
      </Routes>

      <Toaster
        position="top-right"
        toastOptions={{
          duration: 3000,
          style: {
            background: "#0f172a",
            color: "#ffffff",
            border: "1px solid #334155",
            borderRadius: "16px",
            padding: "14px 16px",
            fontWeight: "800",
          },
        }}
      />
    </BrowserRouter>
  );
}

export default App;
