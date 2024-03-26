import api from '../utils/api';
import { useEffect, useState } from 'react';
import Header from '../components/Header';
import {
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';

interface WorkflowResponseProps {
  id: string;
  status: string;
  created_at: number;
  total_jobs: number;
  finished_jobs: number;
}

interface WorkflowProps {
  id: string;
  status: string;
  created_at: Date;
  total_jobs: number;
  finished_jobs: number;
}

const WorkflowsPage = () => {
  const navigate = useNavigate();

  const [workflows, setWorkflows] = useState<WorkflowProps[]>([]);

  useEffect(() => {
    (async () => {
      const res = await api.get<WorkflowResponseProps[]>('/workflow');
      if (res.status !== 200) {
        console.error('Failed to get workflows');
        return;
      }

      const data = res.data.map((prev) => ({
        ...prev,
        created_at: new Date(prev.created_at),
      }));
      setWorkflows(data);
    })();
  }, []);

  return (
    <>
      <Header />
      <div className='container mx-auto mt-4'>
        {workflows.length !== 0 ? (
          <TableContainer component={Paper}>
            <Table
              sx={{ minWidth: 650 }}
              style={{ tableLayout: 'fixed' }}
              aria-label='simple table'>
              <TableHead>
                <TableRow className='bg-white'>
                  <TableCell align='center'>
                    <span className='font-bold text-lg'>ID</span>
                  </TableCell>
                  <TableCell align='center'>
                    <span className='font-bold text-lg'>State</span>
                  </TableCell>
                  <TableCell align='center'>
                    <span className='font-bold text-lg'>Created at</span>
                  </TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {workflows
                  .sort(
                    (a, b) => b.created_at.getTime() - a.created_at.getTime()
                  )
                  .map((workflow) => (
                    <TableRow
                      key={workflow.id}
                      className={'cursor-pointer hover:bg-highlited'}
                      onClick={() => navigate(`/workflow/${workflow.id}`)}>
                      <TableCell align='center'>{workflow.id}</TableCell>
                      <TableCell align='center'>
                        {workflow.status} ({workflow.finished_jobs}/
                        {workflow.total_jobs})
                      </TableCell>
                      <TableCell align='center'>
                        {workflow.created_at.toISOString()}
                      </TableCell>
                    </TableRow>
                  ))}
              </TableBody>
            </Table>
          </TableContainer>
        ) : (
          <div className='text-center text-3xl mt-10 text-black'>
            You did not run any workflows yet
          </div>
        )}
      </div>
    </>
  );
};

export default WorkflowsPage;
