import {
  Accordion,
  AccordionActions,
  AccordionDetails,
  AccordionSummary,
  Button,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import api from '../utils/api';
import { useNavigate } from 'react-router-dom';
import { CodeBlock, github } from 'react-code-blocks';
import { useEffect, useState } from 'react';

interface WorkflowDefinition {
  id: string;
  name: string;
  definition: string;
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

  const handleRunWorkflow = async (workflowDefinitionId: string) => {
    const res = await api.post('/run', { id: workflowDefinitionId });
    if (res.status == 200) {
      navigate(`/workflow/${res.data.workflow_id}`);
    } else {
      console.error('Failed to run workflow');
    }
  };

  return (
    <div className='container mx-auto'>
      {workflows
        .sort((a, b) => parseInt(a.id) - parseInt(b.id))
        .map((workflow) => (
          <Accordion>
            <AccordionSummary
              expandIcon={<ExpandMoreIcon />}
              aria-controls='panel3-content'
              id='panel3-header'>
              {workflow.name}
            </AccordionSummary>
            <AccordionDetails>
              <div className='font-mono text-sm'>
                <CodeBlock
                  text={workflow.definition}
                  language={'python'}
                  theme={github}
                  showLineNumbers={true}
                />
              </div>
            </AccordionDetails>
            <AccordionActions>
              <Button onClick={() => handleRunWorkflow(workflow.id)}>
                Run
              </Button>
            </AccordionActions>
          </Accordion>
        ))}
    </div>
  );
};

export default HomePage;
