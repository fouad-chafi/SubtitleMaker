import { Routes, Route } from 'react-router-dom';
import IndexPage from './views/IndexPage';
import TranscribePage from './views/TranscribePage';
import LibraryPage from './views/LibraryPage';
import SettingsPage from './views/SettingsPage';
import Layout from './components/Layout';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<IndexPage />} />
        <Route path="transcribe/:jobId" element={<TranscribePage />} />
        <Route path="library" element={<LibraryPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  );
}

export default App;
