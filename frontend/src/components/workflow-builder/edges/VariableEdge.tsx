import { memo } from 'react';
import {
  BaseEdge,
  EdgeLabelRenderer,
  getBezierPath,
  type EdgeProps,
} from '@xyflow/react';
import { useWorkflowBuilderStore } from '@/stores';
import type { WorkflowNodeData } from '@/types/workflow-builder';

/**
 * Custom edge that displays variable names flowing between nodes.
 * Shows output variables from the source node that are passed to the target.
 */
function VariableEdgeComponent({
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  style = {},
  markerEnd,
  source,
}: EdgeProps) {
  const { nodes } = useWorkflowBuilderStore();

  // Get the source node to find its outputs
  const sourceNode = nodes.find((n) => n.id === source);
  const sourceData = sourceNode?.data as WorkflowNodeData | undefined;

  // Get outputs from the source node
  let outputs: string[] = [];
  if (sourceData) {
    if ('outputs' in sourceData && Array.isArray(sourceData.outputs)) {
      outputs = sourceData.outputs;
    }
    // For nodes without explicit outputs, use the node ID as the output
    if (outputs.length === 0) {
      outputs = [source];
    }
  }

  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  return (
    <>
      <BaseEdge
        path={edgePath}
        markerEnd={markerEnd}
        style={{
          ...style,
          strokeWidth: 2,
          stroke: outputs.length > 0 ? '#6366f1' : '#94a3b8', // indigo if has vars, slate otherwise
        }}
      />
      {outputs.length > 0 && (
        <EdgeLabelRenderer>
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
              pointerEvents: 'all',
            }}
            className="nodrag nopan"
          >
            <div className="flex flex-wrap gap-1 max-w-[150px] justify-center">
              {outputs.slice(0, 3).map((output) => (
                <span
                  key={output}
                  className="inline-flex items-center rounded-full bg-indigo-100 dark:bg-indigo-900/50 px-2 py-0.5 text-[10px] font-medium text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-700"
                >
                  ${'{'}
                  {output}
                  {'}'}
                </span>
              ))}
              {outputs.length > 3 && (
                <span className="inline-flex items-center rounded-full bg-muted px-2 py-0.5 text-[10px] text-muted-foreground">
                  +{outputs.length - 3}
                </span>
              )}
            </div>
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
}

export const VariableEdge = memo(VariableEdgeComponent);
