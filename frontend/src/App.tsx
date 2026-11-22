import { Navigate, Route, BrowserRouter, Routes } from "react-router-dom";
import { AdminLayout } from "./pages/admin/AdminLayout";
import { AdminLogin } from "./pages/admin/AdminLogin";
import { AttemptDetail } from "./pages/admin/AttemptDetail";
import { Attempts } from "./pages/admin/Attempts";
import { Questions } from "./pages/admin/Questions";
import { Subjects } from "./pages/admin/Subjects";
import { Templates } from "./pages/admin/Templates";
import { TestTakers } from "./pages/admin/TestTakers";
import { ExamHome } from "./pages/exam/ExamHome";
import { ExamLogin } from "./pages/exam/ExamLogin";
import { ExamRunner } from "./pages/exam/ExamRunner";
import { Results } from "./pages/exam/Results";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/exam" replace />} />

        <Route path="/exam/login" element={<ExamLogin />} />
        <Route path="/exam" element={<ExamHome />} />
        <Route path="/exam/attempts/:attemptId" element={<ExamRunner />} />
        <Route path="/exam/attempts/:attemptId/results" element={<Results />} />

        <Route path="/admin/login" element={<AdminLogin />} />
        <Route path="/admin" element={<AdminLayout />}>
          <Route index element={<Navigate to="/admin/subjects" replace />} />
          <Route path="subjects" element={<Subjects />} />
          <Route path="questions" element={<Questions />} />
          <Route path="templates" element={<Templates />} />
          <Route path="attempts" element={<Attempts />} />
          <Route path="attempts/:attemptId" element={<AttemptDetail />} />
          <Route path="testtakers" element={<TestTakers />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
