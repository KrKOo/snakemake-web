import {
  Accordion,
  AccordionActions,
  AccordionDetails,
  AccordionSummary,
  Button,
  InputAdornment,
  TextField,
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

  const handleRunWorkflow = async (workflow: WorkflowDefinition) => {
    const res = await api.post('/run', {
      id: workflow.id,
      input_dir: workflow.input_dir,
      output_dir: workflow.output_dir,
    });
    if (res.status == 200) {
      navigate(`/workflow/${res.data.workflow_id}`);
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
                <TextField
                  required
                  id='outlined-required'
                  label='Input directory'
                  style={{ margin: '0 10px 0 10px' }}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position='start'>
                        s3://root/
                      </InputAdornment>
                    ),
                  }}
                  // value={workflow.input_dir}
                  onChange={(event) =>
                    handleDirInputChange(event, index, 'input_dir')
                  }
                />
                <TextField
                  required
                  id='outlined-required'
                  label='Output directory'
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position='start'>
                        s3://root/
                      </InputAdornment>
                    ),
                  }}
                  // value={workflow.output_dir}
                  onChange={(event) =>
                    handleDirInputChange(event, index, 'output_dir')
                  }
                />
                <div className='font-mono text-sm mt-4'>
                  <CodeBlock
                    text={workflow.definition}
                    language={'python'}
                    theme={github}
                    showLineNumbers={true}
                  />
                </div>
              </AccordionDetails>
              <AccordionActions>
                <Button onClick={() => handleRunWorkflow(workflow)}>
                  <span className='text-lg'>RUN</span>
                </Button>
              </AccordionActions>
            </Accordion>
          ))}
      </div>
    </>
  );
};

export default HomePage;
