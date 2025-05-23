import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Button,
  InputAdornment,
  TextField,
  Grid,
  Alert,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import api from '../utils/api';
import { useNavigate } from 'react-router-dom';
import { CodeBlock, github } from 'react-code-blocks';
import { useEffect, useState } from 'react';
import Header from '../components/Header';

interface WorkflowDefinition {
  id: string;
  name: string;
  definition: string;
  input_dir?: string;
  output_dir?: string;
  alert?: React.ReactNode;
}

const HomePage = () => {
  const navigate = useNavigate();

  const [workflows, setWorkflows] = useState<WorkflowDefinition[]>([]);

  useEffect(() => {
    (async () => {
      const res = await api.get<WorkflowDefinition[]>('/workflow_definition');
      if (res.status !== 200) {
        console.error('Failed to get workflows');
        return;
      }
      setWorkflows(res.data);
    })();
  }, []);

  const setWorkflowAlert = (id: number, alert: React.ReactNode) => {
    const newWorkflows = [...workflows];
    newWorkflows[id].alert = alert;
    setWorkflows(newWorkflows);
  };

  const handleRunWorkflow = async (workflow: WorkflowDefinition, id: number) => {
    if (!workflow.input_dir || !workflow.output_dir) {
      setWorkflowAlert(id, <Alert severity="error">Input and output directory fields are required.</Alert>);
      return;
    }

    const res = await api.post('/run', {
      workflow_definition_id: workflow.id,
      input_dir: workflow.input_dir,
      output_dir: workflow.output_dir,
    });
    if (res.status == 200) {
      setWorkflowAlert(id, null)
      navigate(`/workflow/${res.data.id}`);
    } else {
      console.error('Failed to run workflow');
    }
  };

  const handleDirInputChange = (
    event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
    id: number,
    property: 'input_dir' | 'output_dir'
  ) => {
    const newWorkflows = [...workflows];
    newWorkflows[id][property] = event.target.value;
    setWorkflows(newWorkflows);
  };

  return (
    <>
      <Header />
      <div className='container mx-auto mt-4'>
        {workflows
          .sort((a, b) => parseInt(a.id) - parseInt(b.id))
          .map((workflow, index) => (
            <Accordion key={index}>
              <AccordionSummary
                expandIcon={<ExpandMoreIcon />}
                aria-controls='panel3-content'
                id='panel3-header'
                className='text-lg'>
                {workflow.name}
              </AccordionSummary>
              <AccordionDetails>
                {workflow.alert && <div className='pb-3 w-full'>{workflow.alert}</div>}
                <Grid container spacing={2}>
                  <Grid item xs={3}>
                    <TextField
                      required
                      fullWidth
                      id='outlined-required'
                      label='Input directory'
                      InputProps={{
                        startAdornment: (
                          <InputAdornment position='start'>
                            sda://
                          </InputAdornment>
                        ),
                      }}
                      // value={workflow.input_dir}
                      onChange={(event) =>
                        handleDirInputChange(event, index, 'input_dir')
                      }
                    />
                  </Grid>
                  <Grid item xs={3}>
                  <TextField
                    required
                    fullWidth
                    id='outlined-required'
                    label='Output directory'
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position='start'>
                          s3://inbox/
                        </InputAdornment>
                      ),
                    }}
                    // value={workflow.output_dir}
                    onChange={(event) =>
                      handleDirInputChange(event, index, 'output_dir')
                    }
                  />
                  </Grid>
                  <Grid item xs={1}>
                    <Button 
                      fullWidth
                      style={{ height: '100%' }}
                      variant='outlined'
                      onClick={() => handleRunWorkflow(workflow, index)}>
                      <span className='text-lg'>RUN</span>
                    </Button>
                  </Grid>
                </Grid>
                <div className='font-mono text-sm mt-4'>
                  <CodeBlock
                    text={workflow.definition}
                    language={'python'}
                    theme={github}
                    showLineNumbers={true}
                  />
                </div>
              </AccordionDetails>
            </Accordion>
          ))}
      </div>
    </>
  );
};

export default HomePage;
