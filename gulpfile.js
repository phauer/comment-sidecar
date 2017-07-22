var gulp = require('gulp'),
    livereload = require('gulp-livereload');

gulp.task('refreshCss', function() {
    gulp.src('src/*.css').pipe(livereload());
});
gulp.task('refreshJs', function() {
    gulp.src('src/*.js').pipe(livereload());
});
gulp.task('refreshHtml', function() {
    gulp.src('src/*.html').pipe(livereload());
});
gulp.task('watch', function() {
    livereload.listen();
    gulp.watch(['src/*.css'], ['refreshCss']);
    gulp.watch(['src/*.js'], ['refreshJs']);
    gulp.watch(['src/*.html'], ['refreshHtml']);
});