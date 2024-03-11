import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import api from '../utls/api';
import {
  Box,
  Button,
  Collapse,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import Paper from '@mui/material/Paper';

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
          navigate('/');
        });
    })();
  }, [workflowId, navigate]);

  return (
    <>
      <div className='container mx-auto'>
        <h1 className='text-4xl font-bold'>{workflowId}</h1>

        <TableContainer component={Paper}>
          <Table sx={{ minWidth: 650 }} aria-label='simple table'>
            <TableHead>
              <TableRow>
                <TableCell>ID</TableCell>
                <TableCell align='center'>Name</TableCell>
                <TableCell align='center'>State</TableCell>
                <TableCell align='center'>CreatedAt</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {jobs.map((job, index) => {
                return <Row key={job.id} id={index} row={job} />;
              })}
            </TableBody>
          </Table>
        </TableContainer>
      </div>
    </>
  );
};

function Row(props: { id: number; row: JobInfo }) {
  const { id, row } = props;
  const [open, setOpen] = useState(false);

  return (
    <>
      <TableRow sx={{ '& > *': { borderBottom: 'unset' } }}>
        <TableCell>
          <Button
            aria-label='expand row'
            size='small'
            onClick={() => setOpen(!open)}>
            {/* {open ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />} */}
            V
          </Button>
        </TableCell>
        <TableCell align='center'>{id}</TableCell>
        <TableCell align='center'>{row.id}</TableCell>
        <TableCell align='center'>{row.state}</TableCell>
        <TableCell align='center'>{row.creationTime}</TableCell>
      </TableRow>
      <TableRow>
        <TableCell
          style={{ paddingBottom: 0, paddingTop: 0 }}
          className='bg-black '
          colSpan={6}>
          <Collapse in={open} timeout='auto' unmountOnExit>
            <Box sx={{ margin: 1 }} className='text-white'>
              {row.logs.split('\n').map((i, key) => (
                <pre key={key} className='whitespace-pre-line'>
                  {i}
                </pre>
              ))}
            </Box>
          </Collapse>
        </TableCell>
      </TableRow>
    </>
  );
}

export default WorkflowDetailPage;
