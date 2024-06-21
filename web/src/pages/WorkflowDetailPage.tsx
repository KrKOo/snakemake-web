import { useCallback, useEffect, useState } from 'react';
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
  Tooltip,
} from '@mui/material';
import Paper from '@mui/material/Paper';
import RefreshIcon from '@mui/icons-material/Refresh';
import CancelIcon from '@mui/icons-material/Cancel';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import Header from '../components/Header';

const JobStateToColor: { [state: string]: string } = {
  unknown: 'bg-gray-300',
  queued: 'bg-gray-300',
  initializing: 'bg-blue-300',
  running: 'bg-blue-300',
  paused: 'bg-yellow-300',
  complete: 'bg-green-300',
  executor_error: 'bg-red-300',
  system_error: 'bg-red-300',
  canceled: 'bg-orange-300',
};

interface JobInfo {
  id: string;
  created_at: string;
  state: string;
  logs: string;
}

type WorkflowState = 'UNKNOWN' | 'RUNNING' | 'FINISHED' | 'FAILED' | 'CANCELED';

interface WorfklowDetail {
  id: string;
  created_at: string;
  state: WorkflowState;
  jobs: JobInfo[];
}

const WorkflowDetailPage = () => {
  const { workflowId } = useParams();
  const navigate = useNavigate();

  const [workflowDetail, setWorkflowDetail] = useState<WorfklowDetail>();

  const getJobs = useCallback(() => {
    api
      .get<WorfklowDetail>(`/workflow/${workflowId}`)
      .then((res) => {
        setWorkflowDetail(res.data);
      })
      .catch(() => {
        console.error('Failed to get workflow');
        navigate('/workflows');
      });
  }, [navigate, workflowId]);

  useEffect(() => {
    getJobs();
  }, [getJobs]);

  const handleRefresh = () => {
    getJobs();
  };

  const cancelWorkflowHandler = () => {
    api
      .delete(`/workflow/${workflowId}`)
      .then(() => {
        getJobs();
      })
      .catch(() => {
        console.error('Failed to cancel workflow');
      });
  };

  return (
    <>
      <Header />
      <div className='container mx-auto mt-4'>
        <div className='mb-4 text-3xl text-black'>
          Workflow ID: {workflowId}
        </div>
        <div className='float-right'>
          {workflowDetail?.state == 'RUNNING' && (
            <Tooltip title='Cancel workflow' placement='top'>
              <IconButton
                color='primary'
                size='large'
                onClick={cancelWorkflowHandler}>
                <CancelIcon fontSize='inherit' />
              </IconButton>
            </Tooltip>
          )}
          <Tooltip title='Refresh' placement='top'>
            <IconButton color='primary' size='large' onClick={handleRefresh}>
              <RefreshIcon fontSize='inherit' />
            </IconButton>
          </Tooltip>
        </div>
        {workflowDetail?.jobs.length !== 0 ? (
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
                {workflowDetail?.jobs.map((job) => {
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
        onClick={() => setOpen(!open)}
        className={`hover:brightness-90 ${
          JobStateToColor[job.state.toLowerCase()]
        }`}>
        <TableCell>
          <IconButton aria-label='expand row' size='small'>
            {open ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
          </IconButton>
        </TableCell>
        <TableCell align='center'>{job.id}</TableCell>
        <TableCell align='center'>{job.state}</TableCell>
        <TableCell align='center'>{job.created_at}</TableCell>
      </TableRow>
      <TableRow className='p-0 m-0'>
        <TableCell
          style={{
            padding: 0,
          }}
          className='bg-black'
          colSpan={6}>
          <Collapse in={open} timeout='auto'>
            <div className='max-h-96 overflow-y-scroll px-2 container'>
              <Box sx={{ margin: 1 }} className='text-white'>
                {job.logs.split(/\r\n|\n|\r/).map((i, key) => (
                  <pre key={key} className='whitespace-pre-line'>
                    {i.replaceAll(/\p{C}/gu, '')}
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
