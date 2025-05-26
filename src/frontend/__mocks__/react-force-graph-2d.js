import React from 'react';

const ForceGraph2D = React.forwardRef((props, ref) => {
  return <div data-testid="force-graph-2d" ref={ref}>Force Graph Mock</div>;
});

ForceGraph2D.displayName = 'ForceGraph2D';

export default ForceGraph2D;