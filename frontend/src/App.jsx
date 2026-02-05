import { BrowserRouter } from 'react-router-dom';
import { SCADAProvider } from './contexts/SCADAContext';
import { HistoryProvider } from './contexts/HistoryContext';
import { AlarmProvider } from './contexts/AlarmContext';
import AppRoutes from './routes/AppRoutes';

function App() {
  return (
    <BrowserRouter>
      <SCADAProvider>
        <HistoryProvider>
          <AlarmProvider>
            <AppRoutes />
          </AlarmProvider>
        </HistoryProvider>
      </SCADAProvider>
    </BrowserRouter>
  );
}

export default App;
