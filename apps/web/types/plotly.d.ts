/**
 * Type declarations for plotly packages used with the minimal bundle.
 */

declare module 'plotly.js-basic-dist-min' {
  const Plotly: object
  export default Plotly
}

declare module 'react-plotly.js/factory' {
  import { ComponentType } from 'react'
  export default function createPlotlyComponent(plotly: object): ComponentType<any>
}
