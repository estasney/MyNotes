const path = require('path');
const {CleanWebpackPlugin} = require('clean-webpack-plugin');

module.exports = {
    mode: 'production',
    entry: './index.js',
    output: {
        filename: '[name].[chunkhash].bundle.js',
        path: path.resolve(__dirname, 'dist'),
        clean: true
    },
    module: {
        rules: [
            {
                test: /\.(scss)$/,
                use: [{
                    loader: 'style-loader' // inject CSS to page
                }, {
                    loader: 'css-loader' // translates CSS into CommonJS modules
                }, {
                    loader: 'postcss-loader', // Run postcss actions
                    options: {
                        postcssOptions: {
                            plugins: [
                                "autoprefixer"
                            ]
                        }
                    }
                }, {
                    loader: 'sass-loader' // compiles Sass to CSS
                }]
            },
            {
                test: /\.(woff|woff2|eot|ttf|otf)$/i,
                type: 'asset/resource'
            }

        ]
    },
    plugins: [
            new CleanWebpackPlugin()
        ]
};

