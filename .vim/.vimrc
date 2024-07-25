augroup AutoBuildDocs
    autocmd!
    autocmd BufWritePost *.rst call AutoBuildDocs()
augroup END

function! AutoBuildDocs()
    echomsg 'Building docs...'
    let cmd = 'poetry run bash -c "cd docs && make html"'

    let job = jobstart(cmd, {
        \ 'on_exit': 'BuildDocsComplete',
        \ 'stdout_buffered': v:true,
        \ 'stderr_buffered': v:true,
        \ })
endfunction

function! BuildDocsComplete(job_id, data, event)
    if a:event == 'exit'
        if a:data == 0
            echomsg 'Docs built successfully'
        else
            echoerr 'Error building docs. Exit code: ' . a:data
        endif
    endif
endfunction
