import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import api from '../utils/api';
import {
  Box,
  Collapse,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import Paper from '@mui/material/Paper';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import Header from '../components/Header';

interface JobInfo {
  id: string;
  creationTime: string;
  state: string;
  logs: string;
}

const WorkflowDetailPage = () => {
  const { workflowId } = useParams();
  const navigate = useNavigate();

  const [jobs, setJobs] = useState<JobInfo[]>([]);

  useEffect(() => {
    (async () => {
      api
        .get<JobInfo[]>(`/workflow/${workflowId}/jobs`)
        .then((res) => {
          setJobs(res.data);
        })
        .catch(() => {
          console.error('Failed to get workflow');
          navigate('/workflows');
        });
    })();
  }, [workflowId, navigate]);

  return (
    <>
      <Header />
      <div className='container mx-auto mt-4'>
        <div className='mb-4 text-3xl text-black'>
          Workflow ID: {workflowId}
        </div>
        {jobs.length !== 0 ? (
          <TableContainer component={Paper}>
            <Table sx={{ minWidth: 650 }} aria-label='simple table'>
              <TableHead>
                <TableRow className='bg-white'>
                  <TableCell></TableCell>
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
                {jobs.map((job) => {
                  return <Row key={job.id} job={job} />;
                })}
              </TableBody>
            </Table>
          </TableContainer>
        ) : (
          <div className='text-center text-3xl mt-10 text-black'>
            This workflow did not run any jobs yet
          </div>
        )}
      </div>
    </>
  );
};

function Row(props: { job: JobInfo }) {
  const { job } = props;
  const [open, setOpen] = useState(false);

  return (
    <>
      <TableRow
        sx={{ '& > *': { borderBottom: 'unset' } }}
        onClick={() => setOpen(!open)}>
        <TableCell>
          <IconButton aria-label='expand row' size='small'>
            {open ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
          </IconButton>
        </TableCell>
        <TableCell align='center'>{job.id}</TableCell>
        <TableCell align='center'>{job.state}</TableCell>
        <TableCell align='center'>{job.creationTime}</TableCell>
      </TableRow>
      <TableRow className='p-0 m-0'>
        <TableCell
          style={{
            padding: 0,
          }}
          className='bg-black'
          colSpan={6}>
          <Collapse in={open} timeout='auto' unmountOnExit>
            <div className='max-h-96 overflow-y-scroll px-2'>
              <Box sx={{ margin: 1 }} className='text-white'>
                {job.logs.split('\n').map((i, key) => (
                  <pre key={key} className='whitespace-pre-line'>
                    {i}
                  </pre>
                ))}
              </Box>
            </div>
          </Collapse>
        </TableCell>
      </TableRow>
    </>
  );
}

export default WorkflowDetailPage;
