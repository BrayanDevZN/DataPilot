export function saveToken(token) {
  localStorage.setItem("token", token);
}

export function getToken() {
  return localStorage.getItem("token");
}

export function removeToken() {
  localStorage.removeItem("token");
}

export function saveRegisterData(data) {
  localStorage.setItem("register_data", JSON.stringify(data));
}

export function getRegisterData() {
  const data = localStorage.getItem("register_data");
  return data ? JSON.parse(data) : null;
}

export function removeRegisterData() {
  localStorage.removeItem("register_data");
}

export function saveResetEmail(email) {
  localStorage.setItem("reset_email", email);
}

export function getResetEmail() {
  return localStorage.getItem("reset_email");
}

export function removeResetEmail() {
  localStorage.removeItem("reset_email");
}

export function logout() {
  removeToken();
  removeRegisterData();
  removeResetEmail();
}