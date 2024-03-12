import React from 'react';
import ReactDOM from 'react-dom/client';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import './index.css';

import HomePage from './pages/HomePage';
import WorkflowDetailPage from './pages/WorkflowDetailPage';
import WorkflowsPage from './pages/WorkflowsPage';

const router = createBrowserRouter([
  {
    path: '/',
    element: <HomePage />,
  },
  {
    path: '/workflow/:workflowId',
    element: <WorkflowDetailPage />,
  },
  {
    path: '/workflows',
    element: <WorkflowsPage />,
  },
]);

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>
);
