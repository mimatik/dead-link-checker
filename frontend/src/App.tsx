import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Configs from './pages/Configs';
import Reports from './pages/Reports';
import ReportDetail from './pages/ReportDetail';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="configs" element={<Configs />} />
          <Route path="reports" element={<Reports />} />
          <Route path="reports/:filename" element={<ReportDetail />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
