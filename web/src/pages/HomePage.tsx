import { Button } from '@mui/material';
import api from '../utls/api';
import { useNavigate } from 'react-router-dom';

const HomePage = () => {
  const navigate = useNavigate();

  const handleRunWorkflow = async () => {
    const res = await api.post('/run');
    if (res.status == 200) {
      navigate(`/workflow/${res.data.workflow_id}`);
    } else {
      console.error('Failed to run workflow');
    }
  };

  return (
    <>
      <h1 className='text-4xl font-bold'>Home</h1>
      <Button variant='contained' color='primary' onClick={handleRunWorkflow}>
        Run Workflow
      </Button>
    </>
  );
};

export default HomePage;
