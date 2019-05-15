declare namespace tf.hparams {
  export interface Schema {
    hparamColumn: Array<{
      hparamInfo: Object,
      displayed: bool,
    }>,
    metricColumn: Array<{
      metricInfo: Object,
      displayed: bool,
    }>,
    visibleSchema: {
      hparamInfos: Array<Object>,
      metricInfos: Array<Object>,
    }
    loaded: bool,
  }
}
