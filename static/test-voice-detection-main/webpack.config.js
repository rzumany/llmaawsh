const path = require('path');
const CopyWebpackPlugin = require('copy-webpack-plugin');
const HtmlWebpackPlugin = require('html-webpack-plugin');

module.exports = (env, argv) => {
  const isProduction = argv.mode === 'production';
  console.log(`production: ${isProduction}`);

  return {
    entry: './src/index.ts',
    module: {
      rules: [
        {
          test: /\.tsx?$/,
          use: 'ts-loader',
          exclude: /node_modules/,
        },
        {
          test: /\.css$/,
          use: ['style-loader', 'css-loader'],
        },
      ],
    },
    resolve: {
      extensions: ['.tsx', '.ts', '.js'],
    },
    output: {
      filename: 'bundle.js',
      path: path.resolve(__dirname, 'dist'),
      publicPath: argv.mode === 'production' ? '/app/static/test-voice-detection-main/dist/' : '/',
    },
    plugins: [
      new HtmlWebpackPlugin({
        template: './src/index.html',
      }),
      new CopyWebpackPlugin({
        patterns: [
          { from: "node_modules/web-voice-detection/dist/worklet.js", to: "[name][ext]" },
          { from: "node_modules/web-voice-detection/dist/*.onnx", to: "[name][ext]", },
          { from: "node_modules/web-voice-detection/dist/*.wasm", to: "[name][ext]" },
          { from: "./src/favicon.ico", to: "[name][ext]" },
        ],
      }),
    ],
    devServer: {
      static: "./dist"
    },
    ignoreWarnings: [
      {
        module: /node_modules\/web-voice-detection\/dist/,
        message: /Critical dependency: require function is used in a way in which dependencies cannot be statically extracted/,
      },
    ],
  }
};
