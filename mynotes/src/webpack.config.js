const path = require('path');
const {CleanWebpackPlugin} = require('clean-webpack-plugin');
const HtmlWebpackPlugin = require("html-webpack-plugin");
const webpack = require("webpack");

const baseConfig = {
    mode: 'none',
    entry: './index.js',
    output: {
        filename: '[name].[chunkhash].bundle.js',
        path: path.resolve(__dirname, "..", "..", "docs", "static", "dist"),
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
    plugins: []
};



module.exports = (env, argv) => {

    baseConfig.mode = argv.mode ? argv.mode : 'development';
    const htmlPluginOptions = {
        filename: path.resolve(__dirname, "..", "..", "docs", "index.html"),
        template: path.resolve(__dirname, "index_built.html"),
        publicPath: baseConfig.mode === "development" ? "/static/dist/" : "/MyNotes/static/dist/",
        scriptLoading: 'blocking',
        minify: false,
        minifyCSS: true
    };
    const mainPageUrl = baseConfig.mode === "development"
        ? "http://localhost:8000"
        : "https://estasney.github.io/MyNotes/"
    baseConfig.plugins.push(new HtmlWebpackPlugin(htmlPluginOptions));
    baseConfig.plugins.push(new CleanWebpackPlugin());
    baseConfig.plugins.push(new webpack.DefinePlugin({"process.env.MAIN_PAGE": JSON.stringify(mainPageUrl)}))

    return baseConfig;
};


